#!/usr/bin/env python3

import os
import sys
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main


class TestGetUrlSize:
    """Tests for get_url_size function"""
    
    @patch('main.requests.head')
    def test_get_url_size_success(self, mock_head):
        """Test successful retrieval of file size"""
        mock_response = Mock()
        mock_response.headers = {'Content-Length': '12345'}
        mock_response.raise_for_status = Mock()
        mock_head.return_value = mock_response
        
        size = main.get_url_size("https://example.com/file.dat")
        assert size == 12345
        mock_head.assert_called_once_with("https://example.com/file.dat", allow_redirects=True, timeout=30)
    
    @patch('main.requests.head')
    def test_get_url_size_no_content_length(self, mock_head):
        """Test when Content-Length header is missing"""
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()
        mock_head.return_value = mock_response
        with pytest.raises(RuntimeError):
            main.get_url_size("https://example.com/file.dat")
    
    @patch('main.requests.head')
    def test_get_url_size_error(self, mock_head):
        """Test error handling"""
        mock_head.side_effect = Exception("Connection error")
        with pytest.raises(Exception):
            main.get_url_size("https://example.com/file.dat")


class TestGetFileSize:
    """Tests for get_file_size function"""
    
    def test_get_file_size_existing(self, tmp_path):
        """Test getting size of existing file"""
        test_file = tmp_path / "test.dat"
        test_file.write_bytes(b"test content" * 100)
        
        size = main.get_file_size(test_file)
        assert size == len(b"test content" * 100)
    
    def test_get_file_size_nonexistent(self, tmp_path):
        """Test getting size of non-existing file"""
        test_file = tmp_path / "nonexistent.dat"
        
        size = main.get_file_size(test_file)
        assert size == 0


class TestNeedDownload:
    """Tests for need_download function"""
    
    @patch('main.get_url_size')
    @patch('main.get_file_size')
    @patch('main.log')
    def test_need_download_file_not_exists(self, mock_log, mock_get_file_size, mock_get_url_size, tmp_path):
        """Test when local file doesn't exist"""
        local_file = tmp_path / "test.dat"
        mock_get_file_size.return_value = 0
        
        result = main.need_download("https://example.com/file.dat", local_file)
        assert result is True
        mock_log.info.assert_called()
    
    @patch('main.get_url_size')
    @patch('main.get_file_size')
    @patch('main.log')
    def test_need_download_sizes_different(self, mock_log, mock_get_file_size, mock_get_url_size, tmp_path):
        """Test when remote and local sizes differ"""
        local_file = tmp_path / "test.dat"
        local_file.write_bytes(b"test")
        mock_get_url_size.return_value = 1000
        mock_get_file_size.return_value = 500
        
        result = main.need_download("https://example.com/file.dat", local_file)
        assert result is True
        mock_log.info.assert_called()
    
    @patch('main.get_url_size')
    @patch('main.get_file_size')
    def test_need_download_sizes_same(self, mock_get_file_size, mock_get_url_size, tmp_path):
        """Test when remote and local sizes are the same"""
        local_file = tmp_path / "test.dat"
        local_file.write_bytes(b"test")
        mock_get_url_size.return_value = 1000
        mock_get_file_size.return_value = 1000
        
        result = main.need_download("https://example.com/file.dat", local_file)
        assert result is False
    
    @patch('main.get_url_size')
    @patch('main.get_file_size')
    def test_need_download_url_size_none(self, mock_get_file_size, mock_get_url_size, tmp_path):
        """Test when URL size cannot be determined"""
        local_file = tmp_path / "test.dat"
        local_file.write_bytes(b"test")
        # get_url_size now raises when size cannot be determined
        mock_get_url_size.side_effect = Exception("No size")
        mock_get_file_size.return_value = 500

        with pytest.raises(Exception):
            main.need_download("https://example.com/file.dat", local_file)


class TestDownloadFile:
    """Tests for download_file function"""
    
    @patch('main.requests.get')
    @patch('main.get_file_size')
    def test_download_file_success(self, mock_get_file_size, mock_get, tmp_path):
        """Test successful file download"""
        test_file = tmp_path / "downloaded.dat"
        mock_response = Mock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_get_file_size.return_value = 100
        
        result = main.download_file("https://example.com/file.dat", test_file)
        assert result is True
        assert test_file.exists()
        mock_get.assert_called_once_with("https://example.com/file.dat", allow_redirects=True, timeout=20, stream=True)
    
    @patch('main.requests.get')
    @patch('main.get_file_size')
    def test_download_file_empty(self, mock_get_file_size, mock_get, tmp_path):
        """Test when downloaded file is empty"""
        test_file = tmp_path / "empty.dat"
        mock_response = Mock()
        mock_response.iter_content.return_value = []
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_get_file_size.return_value = 0
        with pytest.raises(RuntimeError):
            main.download_file("https://example.com/file.dat", test_file)
    
    @patch('main.requests.get')
    def test_download_file_error(self, mock_get, tmp_path):
        """Test download error handling"""
        test_file = tmp_path / "error.dat"
        mock_get.side_effect = Exception("Network error")
        with pytest.raises(Exception):
            main.download_file("https://example.com/file.dat", test_file)


class TestCopyFileToContainer:
    """Tests for copy_file_to_container function"""
    
    @patch('main.os.unlink')
    @patch('builtins.open', new_callable=mock_open, read_data=b'tar data')
    def test_copy_file_to_container_success(self, mock_file, mock_unlink, tmp_path):
        """Test successful file copy to container"""
        test_file = tmp_path / "test.dat"
        test_file.write_bytes(b"test content")
        
        mock_container = Mock()
        mock_container.exec_run.return_value = Mock(exit_code=0)
        mock_container.put_archive.return_value = True
        
        result = main.copy_file_to_container(mock_container, test_file, "/app/bin/test.dat")
        assert result is True
        mock_container.exec_run.assert_called_once_with("mkdir -p /app/bin", user="root")
        mock_container.put_archive.assert_called_once()
        mock_unlink.assert_called()
    
    def test_copy_file_to_container_error(self, tmp_path):
        """Test error handling in file copy"""
        test_file = tmp_path / "test.dat"
        test_file.write_bytes(b"test content")
        
        mock_container = Mock()
        mock_container.exec_run.side_effect = Exception("Docker error")

        with pytest.raises(Exception):
            main.copy_file_to_container(mock_container, test_file, "/app/bin/test.dat")


class TestRestartXray:
    """Tests for restart_xray function"""
    
    @patch('main.log')
    def test_restart_xray_success(self, mock_log):
        """Test successful xray restart"""
        mock_container = Mock()
        mock_pgrep_result = Mock()
        mock_pgrep_result.exit_code = 0
        mock_pgrep_result.output = b"12345"
        mock_kill_result = Mock()
        mock_kill_result.exit_code = 0
        
        mock_container.exec_run.side_effect = [mock_pgrep_result, mock_kill_result]
        
        result = main.restart_xray(mock_container)
        assert result is True
        assert mock_container.exec_run.call_count == 2
        mock_log.info.assert_called()
    
    def test_restart_xray_no_process(self):
        """Test when xray process is not found"""
        mock_container = Mock()
        mock_pgrep_result = Mock()
        mock_pgrep_result.exit_code = 1
        mock_container.exec_run.return_value = mock_pgrep_result
        with pytest.raises(RuntimeError):
            main.restart_xray(mock_container)
    
    def test_restart_xray_empty_pid(self):
        """Test when pgrep returns empty output"""
        mock_container = Mock()
        mock_pgrep_result = Mock()
        mock_pgrep_result.exit_code = 0
        mock_pgrep_result.output = b""
        mock_container.exec_run.return_value = mock_pgrep_result
        with pytest.raises(RuntimeError):
            main.restart_xray(mock_container)
    
    def test_restart_xray_error(self):
        """Test error handling in restart"""
        mock_container = Mock()
        mock_container.exec_run.side_effect = Exception("Docker error")
        with pytest.raises(Exception):
            main.restart_xray(mock_container)


class TestGetContainer:
    """Tests for get_container function"""
    
    def test_get_container_found(self):
        """Test when container is found"""
        mock_client = Mock()
        mock_container = Mock()
        mock_client.containers.list.return_value = [mock_container]
        # set module-level docker_client
        main.docker_client = mock_client

        result = main.get_container("3x-ui")
        assert result == mock_container
        mock_client.containers.list.assert_called_once_with(filters={"name": "3x-ui"})
    
    @patch('main.log')
    def test_get_container_not_found(self, mock_log):
        """Test when container is not found"""
        mock_client = Mock()
        mock_client.containers.list.return_value = []
        main.docker_client = mock_client

        with pytest.raises(RuntimeError):
            main.get_container("3x-ui")
    
    def test_get_container_error(self):
        """Test error handling"""
        mock_client = Mock()
        mock_client.containers.list.side_effect = Exception("Docker error")
        main.docker_client = mock_client
        with pytest.raises(Exception):
            main.get_container("3x-ui")


class TestUpdateGeo:
    """Tests for update_geo function"""
    
    @patch('main.restart_xray')
    @patch('main.copy_file_to_container')
    @patch('main.download_file')
    @patch('main.need_download')
    def test_update_geo_with_downloads(self, mock_need_download, mock_download_file, 
                                       mock_copy_file, mock_restart_xray, tmp_path):
        """Test update_geo when files need to be downloaded"""
        # Setup
        workdir = tmp_path / "geo"
        workdir.mkdir()
        
        with patch('main.WORKDIR', workdir):
            # Mock need_download to return True for all files
            mock_need_download.return_value = True
            mock_download_file.return_value = True
            mock_copy_file.return_value = True
            mock_restart_xray.return_value = True

            for geo_file in main.GEO_FILES:
                filename = geo_file["filename"]
                local_file = workdir / filename
                local_file.write_bytes(b"dummy data")
                print(local_file)
            
            mock_container = Mock()
            mock_docker_client = Mock()

            # Ensure get_container finds the mocked container
            mock_docker_client.containers.list.return_value = [mock_container]

            # set module-level docker_client and call update_geo()
            main.docker_client = mock_docker_client
            result = main.update_geo()
            assert result is True
            # Should attempt to download all 4 geo files
            assert mock_download_file.call_count == len(main.GEO_FILES)
            # Should copy all downloaded files
            assert mock_copy_file.call_count == len(main.GEO_FILES)
            # Should restart xray once after all files are copied
            mock_restart_xray.assert_called_once()
    
    @patch('main.need_download')
    def test_update_geo_no_downloads(self, mock_need_download, tmp_path):
        """Test update_geo when no files need updating"""
        workdir = tmp_path / "geo"
        workdir.mkdir()
        
        with patch('main.WORKDIR', workdir):
            mock_need_download.return_value = False
            
            mock_container = Mock()
            mock_docker_client = Mock()

            # Ensure get_container finds the mocked container
            mock_docker_client.containers.list.return_value = [mock_container]

            main.docker_client = mock_docker_client
            result = main.update_geo()
            assert result is False
    
    @patch('main.copy_file_to_container')
    @patch('main.download_file')
    @patch('main.need_download')
    @patch('main.get_container_file_size')
    def test_update_geo_copy_failure(self, mock_get_container_file_size, mock_need_download, 
                                     mock_download_file, mock_copy_file, tmp_path):
        """Test update_geo when file copy fails"""
        workdir = tmp_path / "geo"
        workdir.mkdir()
        
        with patch('main.WORKDIR', workdir):
            mock_need_download.return_value = True
            mock_download_file.return_value = True
            mock_get_container_file_size.return_value = 100
            mock_copy_file.side_effect = Exception("copy failed")  # Copy fails
            
            mock_container = Mock()
            mock_docker_client = Mock()

            # Ensure get_container finds the mocked container
            mock_docker_client.containers.list.return_value = [mock_container]

            main.docker_client = mock_docker_client
            with pytest.raises(Exception, match="copy failed"):
                main.update_geo()


class TestMain:
    """Tests for main function"""
    
    @patch('main.stop_event')
    @patch('main.log')
    @patch('sys.argv', ['main.py', '--delay', '5'])
    def test_main_with_delay_flag(self, mock_log, mock_stop_event):
        """Test main function with '--delay' parameter"""
        # Simulate shutdown requested during initial delay
        mock_stop_event.wait.return_value = True

        # Run main; it should return early because stop_event.wait returned True
        main.main()

        mock_stop_event.wait.assert_called_once_with(5)
        mock_log.info.assert_called()

    @patch('main.stop_event')
    @patch('main.random.randint', return_value=42)
    @patch('main.log')
    @patch('sys.argv', ['main.py', '--delay'])
    def test_main_with_no_value_delay(self, mock_log, mock_randint, mock_stop_event):
        """Test main function with '--delay' without a numeric value"""
        # Simulate shutdown requested during initial delay
        mock_stop_event.wait.return_value = True

        # Run main; it should compute delay using random.randint and return early
        main.main()

        mock_randint.assert_called_once_with(10, 60)
        mock_stop_event.wait.assert_called_once_with(42)
        mock_log.info.assert_called()
    
    @patch('main.docker.from_env')
    @patch('main.log')
    @patch('sys.argv', ['main.py'])
    def test_main_docker_connection_error(self, mock_log, mock_docker_from_env):
        """Test main function when Docker connection fails"""
        mock_docker_from_env.side_effect = Exception("Docker connection error")
        
        with pytest.raises(SystemExit):
            main.main()

        mock_log.error.assert_called()

