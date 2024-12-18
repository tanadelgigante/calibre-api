# Calibre Library API

## Overview
**Calibre Library API** is a FastAPI application designed to manage and serve data from a Calibre library database. It can function both as a standalone application and as a plug-in for **[Civil Servant](https://github.com/tanadelgigante/civil-servant)**.

## Features
- **CORS Configuration**: Configurable CORS middleware to handle cross-origin requests.
- **Standalone or Plug-in**: Can be run as a standalone server or integrated as a plug-in for another FastAPI application.
- **Caching**: Implements persistent caching for improved performance.
- **Token-based Authentication**: Secures endpoints with token-based authentication.

## Application Information
- **Name**: Calibre Library API
- **Version**: 1.0.0
- **Author**: @ilgigante77
- **Website**: [https://github.com/tanadelgigante/calibre-api](https://github.com/tanadelgigante/calibre-api)

## License
This project is licensed under the GPL 3 License. See the [LICENSE](LICENSE) file for details.

## Getting Started

### Prerequisites
- Python 3.9+
- FastAPI
- Docker (optional)

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/calibre-library-api.git
    cd calibre-library-api
    ```

2. **Install the required Python packages**:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1. **Environment Variables**:
   Ensure the necessary environment variables are set, such as `CALIBRE_LIBRARY_PATH`.

2. **Create the `setup.sh` script**:
   Create a `setup.sh` script in the project directory to handle any system setup required for the module.

### Running the Server

1. **Run Locally**:
    ```bash
    python main.py
    ```

2. **Using Docker**:
   Create a `Dockerfile`:
    ```dockerfile
    FROM python:3.9-slim

    WORKDIR /app

    COPY . .

    RUN pip install --no-cache-dir -r requirements.txt

    EXPOSE 8000

    CMD ["python", "main.py"]
    ```

   Build and run the Docker container:
    ```bash
    docker build -t calibre-library-api .
    docker run -p 8000:8000 calibre-library-api
    ```

### Usage

#### API Endpoints

- **GET /statistics**:
    ```
    curl http://localhost:8000/statistics?token=your_token
    ```

    Response:
    ```json
    {
      "status": "success",
      "data": { ... }
    }
    ```

- **GET /books/search**:
    ```
    curl http://localhost:8000/books/search?title=BookTitle&author=AuthorName&token=your_token
    ```

    Response:
    ```json
    {
      "status": "success",
      "data": [ ... ]
    }
    ```

### Integrating as a Plug-in

To use Calibre Library API as a plug-in for **Civil Servant**, ensure `register(app)` is called in the main application.

```python
# In Civil Servant's main application
from calibre_library_api import register

app = FastAPI()
register(app)

```

### Debugging

- The server provides debug information in the console output. Look for `[INFO]`, `[DEBUG]`, and `[WARNING]` messages to understand the server's behavior and troubleshoot issues.

### Contributing
Contributions are welcome! Please fork the repository and submit pull requests for any enhancements or bug fixes.

### License
This project is licensed under the GPL 3.0 License. See the [LICENSE](LICENSE) file for details.

### Disclaimer
This project is released "as-is" and the author is not responsible for damage, errors or misuse. This project is not affiliated neither with Calibre nor Calibre Web nor CWA nor any other derivative Calibre projects.

## Contact
For more information, visit [https://github.com/tanadelgigante/calibre-api](https://github.com/tanadelgigante/calibre-api)
