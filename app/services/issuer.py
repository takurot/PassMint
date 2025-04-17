import uuid
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.future import select

from ..models.models import Pass, Design
from ..utils.qrcode import generate_qr_png_base64
from ..schemas.passes import CreatePassResponse, Platforms, PlatformInfo
from .apple_pass import apple_pass_signer
from .google_wallet import google_wallet_service


class IssuerService:
    async def issue_pass(
        self, 
        session: AsyncSession,
        user_id: str,
        design_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CreatePassResponse:
        """
        Issue a new pass for both Apple and Google platforms
        
        Args:
            session: Database session
            user_id: User ID
            design_id: Design ID
            metadata: Optional metadata
            
        Returns:
            CreatePassResponse with pass details
        """
        # Get design details
        design = await self._get_design(session, design_id)
        if not design:
            raise ValueError(f"Design not found: {design_id}")
            
        # Generate pass ID
        pass_id = str(uuid.uuid4())
        
        # Platforms dict to store results
        platforms = Platforms()
        
        # Try to generate Apple Wallet pass
        try:
            serial, deep_link, _ = await apple_pass_signer.generate_pass(
                design.template_json, pass_id, metadata
            )
            
            # Save to database
            apple_pass = Pass(
                id=uuid.UUID(pass_id),
                user_id=uuid.UUID(user_id),
                design_id=uuid.UUID(design_id),
                platform="apple",
                serial=serial,
                deep_link=deep_link,
                expires_at=design.template_json.get("expires_at")
            )
            session.add(apple_pass)
            
            # Add to response
            platforms.apple = PlatformInfo(
                deep_link=deep_link,
                serial=serial
            )
        except Exception as e:
            print(f"Error generating Apple Pass: {e}")
            # Continue with Google Wallet
            
        # Try to generate Google Wallet pass
        try:
            deep_link = await google_wallet_service.create_generic_pass(
                design.template_json, pass_id, metadata
            )
            
            # Save to database
            google_pass = Pass(
                id=uuid.UUID(pass_id),
                user_id=uuid.UUID(user_id),
                design_id=uuid.UUID(design_id),
                platform="google",
                serial=f"GP-{uuid.uuid4().hex[:8].upper()}",
                deep_link=deep_link,
                expires_at=design.template_json.get("expires_at")
            )
            session.add(google_pass)
            
            # Add to response
            platforms.google = PlatformInfo(
                deep_link=deep_link
            )
        except Exception as e:
            print(f"Error generating Google Wallet pass: {e}")
            
        # Commit to save both passes
        await session.commit()
        
        # If no passes were created, raise error
        if not platforms.apple and not platforms.google:
            raise ValueError("Failed to create passes for all platforms")
            
        # Generate QR code with the first available deep link
        deep_link = (platforms.apple.deep_link if platforms.apple else
                    platforms.google.deep_link if platforms.google else None)
                    
        qr_png = generate_qr_png_base64(deep_link) if deep_link else ""
        
        # Determine expiration from design
        expires_at = design.template_json.get("expires_at")
        
        # Create response
        response = CreatePassResponse(
            pass_id=pass_id,
            platforms=platforms,
            qr_png=qr_png,
            expires_at=expires_at
        )
        
        return response
    
    async def update_pass(
        self,
        session: AsyncSession,
        pass_id: str,
        fields: Dict[str, Any]
    ) -> bool:
        """
        Update an existing pass
        
        Args:
            session: Database session
            pass_id: Pass ID to update
            fields: Fields to update
            
        Returns:
            True if successful
        """
        # In a full implementation, this would:
        # 1. Get the pass details
        # 2. Update the pass in the appropriate platform
        # 3. Update the database record
        
        # For now, we'll just update the last_updated timestamp
        stmt = update(Pass).where(Pass.id == uuid.UUID(pass_id)).values(
            last_updated=datetime.utcnow()
        )
        
        result = await session.execute(stmt)
        await session.commit()
        
        return result.rowcount > 0
    
    async def _get_design(self, session: AsyncSession, design_id: str) -> Optional[Design]:
        """Get design from database"""
        stmt = select(Design).where(Design.id == uuid.UUID(design_id))
        result = await session.execute(stmt)
        return result.scalars().first()
        

# Create a singleton instance
issuer_service = IssuerService() 