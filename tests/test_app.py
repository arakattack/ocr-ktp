import os
import unittest
from unittest.mock import patch
from app import app, validate_api_key

class FlaskTestCase(unittest.TestCase):

    API_KEY = '67BD92FF-9408-43C4-A9F3-8CC942694F1E'
    FILE_PATH = 'tests/sample_ktp.png'

    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_validate_api_key(self):
        self.assertTrue(validate_api_key(self.API_KEY))
        self.assertFalse(validate_api_key('wrong_key'))

    def test_hello(self):
        """Test the root endpoint to ensure it's responding correctly."""
        response = self.client.get('/', headers={'X-API-KEY': self.API_KEY})
        print(response.data)
        self.assertEqual(response.status_code, 200)

    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.client.get('/healthz', headers={'X-API-KEY': self.API_KEY})
        print(response.data)
        self.assertEqual(response.status_code, 200)

    def test_invalid_image_file_type(self):
        """Test invalid image file extension."""
        with open('tests/test.txt', 'rb') as f:
            response = self.client.post("/", data={'image': (f, 'test.txt')}, headers={'X-API-KEY': self.API_KEY})
            print(response.data)
            self.assertEqual(response.status_code, 500)

    def test_invalid_mime_type(self):
        """Test invalid MIME type for an image file."""
        with open('tests/test.bmp', 'rb') as f:
            response = self.client.post("/", data={'image': (f, 'test.bmp')}, headers={'X-API-KEY': self.API_KEY})
            print(response.data)
            self.assertEqual(response.status_code, 500)

    def test_exception_handling(self):
        """Test handling of unexpected exceptions."""
        with patch('app.upload_image', side_effect=Exception("Unexpected Error")):
            with open(self.FILE_PATH, 'rb') as f:
                response = self.client.post("/", data={'image': (f, 'sample_ktp.png')}, headers={'X-API-KEY': self.API_KEY})
                print(response.data)
                self.assertEqual(response.status_code, 200)

    def test_method_not_allowed(self):
        """Test invalid method used (PUT instead of POST)."""
        response = self.client.put("/", headers={'X-API-KEY': self.API_KEY})
        print(response.data)
        self.assertEqual(response.status_code, 405)

    def test_missing_image_data(self):
        """Test missing image data in the request."""
        response = self.client.post("/", headers={'X-API-KEY': self.API_KEY}, data={})
        print(response.data)
        self.assertEqual(response.status_code, 400)

    def test_no_file_selected(self):
        """Test empty file in the request."""
        response = self.client.post("/", headers={'X-API-KEY': self.API_KEY}, data={'image': (b'', '')})
        print(response.data)
        self.assertEqual(response.status_code, 400)

    @patch('app.upload_image')
    def test_process_document(self, mock_upload_image):
        """Test the document processing functionality."""
        mock_response = {
            "error": False,
            "message": "Proses OCR Berhasil",
            "result": {
                "nik": "3026061812510006",
                "nama": "WIDIARSO",
                "tempat_lahir": "PEMALANG,",
                "tgl_lahir": "18-12-1959",
                "jenis_kelamin": "LAKI-LAKI",
                "agama": "ISLAM",
                "status_perkawinan": "KAWIN",
                "pekerjaan": "KARYAWAN SWASTA",
                "alamat": {
                    "name": "SKU JLSUMATRA BLOK B78/15",
                    "rt_rw": "0037004",
                    "kel_desa": "MEKARSARI",
                    "kecamatan": "TAMBUN SELATAN",
                    "kabupaten": "KABUPATEN BEKASI",
                    "provinsi": "PROVINSI JAWA BARAT\n-"
                }
            }
        }
        mock_upload_image.return_value = mock_response

        with open(self.FILE_PATH, 'rb') as f:
            response = self.client.post("/", data={'image': (f, 'sample_ktp.png')}, headers={'X-API-KEY': self.API_KEY})
            # Convert the response data to a dictionary
            response_data = response.get_json()
            # Exclude time_elapsed from the comparison
            response_data['result'].pop('time_elapsed', None)
            print(response_data)

            self.assertEqual(response_data, mock_response)


if __name__ == '__main__':
    unittest.main()
