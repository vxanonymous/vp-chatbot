import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app, lifespan


class TestMain:
    
    def test_app_initialization(self):
        assert app is not None
        assert app.title is not None
        assert app.version is not None
    
    @pytest.mark.asyncio
    async def test_lifespan_with_mongodb(self):
        with patch('app.main.settings') as mock_settings:
            mock_settings.skip_mongodb_connection = False
            
            with patch('app.main.connect_to_mongo', new_callable=AsyncMock) as mock_connect:
                with patch('app.main.close_mongo_connection', new_callable=AsyncMock) as mock_close:
                    async with lifespan(app):
                        mock_connect.assert_called_once()
                    
                    mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_without_mongodb(self):
        with patch('app.main.settings') as mock_settings:
            mock_settings.skip_mongodb_connection = True
            
            with patch('app.main.connect_to_mongo', new_callable=AsyncMock) as mock_connect:
                with patch('app.main.close_mongo_connection', new_callable=AsyncMock) as mock_close:
                    async with lifespan(app):
                        mock_connect.assert_not_called()
                    
                    mock_close.assert_not_called()
    
    def test_app_routes_registered(self):
        routes = [route.path for route in app.routes]
        
        assert any("/health" in route for route in routes)
        assert any("/api/v1/auth" in route for route in routes)
        assert any("/api/v1/conversations" in route for route in routes)
        assert any("/api/v1/chat" in route for route in routes)
    
    def test_cors_middleware_configured(self):
        from fastapi.middleware.cors import CORSMiddleware
        
        middleware_found = False
        for middleware in app.user_middleware:
            if hasattr(middleware, 'cls') and middleware.cls == CORSMiddleware:
                middleware_found = True
                break
        
        assert middleware_found

