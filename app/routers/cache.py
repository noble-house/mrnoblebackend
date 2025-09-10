from fastapi import APIRouter, Depends, HTTPException
from ..services.auth import get_current_admin
from ..services.cache import cache_service
from .. import models
from ..services.logger import log_business_event

router = APIRouter(prefix="/cache", tags=["cache"])

@router.get("/status")
def get_cache_status(current_admin: models.Admin = Depends(get_current_admin)):
    """Get cache service status."""
    return {
        "connected": cache_service.connected,
        "redis_url": cache_service.redis_client.connection_pool.connection_kwargs.get('host', 'unknown') if cache_service.connected else None
    }

@router.post("/clear")
def clear_cache(current_admin: models.Admin = Depends(get_current_admin)):
    """Clear all cache entries."""
    if not cache_service.connected:
        raise HTTPException(status_code=503, detail="Cache service not available")
    
    try:
        # Clear all keys (use with caution in production)
        cleared_count = cache_service.clear_pattern("*")
        
        log_business_event("cache_cleared", "cache", None, admin_id=current_admin.id, keys_cleared=cleared_count)
        
        return {"message": f"Cache cleared successfully. {cleared_count} keys removed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.post("/clear/{entity_type}")
def clear_entity_cache(entity_type: str, current_admin: models.Admin = Depends(get_current_admin)):
    """Clear cache entries for a specific entity type."""
    if not cache_service.connected:
        raise HTTPException(status_code=503, detail="Cache service not available")
    
    try:
        cleared_count = cache_service.clear_pattern(f"*{entity_type}*")
        
        log_business_event("cache_cleared_entity", "cache", None, 
                          admin_id=current_admin.id, entity_type=entity_type, keys_cleared=cleared_count)
        
        return {"message": f"Cache cleared for {entity_type}. {cleared_count} keys removed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/stats")
def get_cache_stats(current_admin: models.Admin = Depends(get_current_admin)):
    """Get cache statistics."""
    if not cache_service.connected:
        raise HTTPException(status_code=503, detail="Cache service not available")
    
    try:
        # Get basic Redis info
        info = cache_service.redis_client.info()
        
        return {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")
