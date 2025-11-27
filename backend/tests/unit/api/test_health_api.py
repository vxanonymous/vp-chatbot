import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.api.health import health_check, root


class TestHealthAPI:
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        result = await health_check()
        assert "status" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_health_check_database_connected(self):
        with patch('app.api.health.get_database') as mock_get_db:
            mock_db = MagicMock()
            mock_db.client.server_info = AsyncMock(return_value={"version": "5.0"})
            mock_get_db.return_value = mock_db
            
            result = await health_check()
            assert result["status"] in ["healthy", "unhealthy"]
            assert "database" in result
    
    @pytest.mark.asyncio
    async def test_health_check_database_disconnected(self):
        with patch('app.api.health.get_database') as mock_get_db:
            mock_get_db.return_value = None
            
            result = await health_check()
            assert result["status"] == "unhealthy"
            assert result["database"] == "disconnected"
    
    @pytest.mark.asyncio
    async def test_health_check_database_error(self):
        with patch('app.api.health.get_database') as mock_get_db:
            mock_db = MagicMock()
            mock_db.client.server_info = AsyncMock(side_effect=Exception("Connection failed"))
            mock_get_db.return_value = mock_db
            
            result = await health_check()
            assert result["status"] == "unhealthy"
            assert result["database"] == "error"
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        result = await root()
        assert "message" in result
        assert "version" in result
        assert "endpoints" in result

