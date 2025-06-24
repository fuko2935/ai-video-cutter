{pkgs}: {
  channel = "stable-23.11";
  packages = [
    pkgs.nodejs_20
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv
    pkgs.redis
    pkgs.ffmpeg
  ];
  
  env = {
    PYTHON_VERSION = "3.11";
    NODE_VERSION = "20";
  };
  
  idx = {
    extensions = [
      "ms-python.python"
      "dbaeumer.vscode-eslint"
      "esbenp.prettier-vscode"
    ];
    
    workspace = {
      onCreate = {
        install-deps = ''
          # Python virtual environment oluştur
          python -m venv backend/venv
          
          # Backend bağımlılıklarını yükle
          cd backend
          source venv/bin/activate
          pip install -r requirements.txt
          cd ..
          
          # Frontend bağımlılıklarını yükle
          cd frontend
          npm install
          cd ..
          
          # Gerekli klasörleri oluştur
          mkdir -p backend/uploads backend/processed
          
          # .env dosyasını oluştur
          if [ ! -f .env ]; then
            cp .env.example .env
            echo "⚠️  .env dosyası oluşturuldu. GEMINI_API_KEY'i güncellemeyi unutmayın!"
          fi
        '';
      };
      
      onStart = {
        start-redis = ''
          # Redis'i arka planda başlat
          redis-server --daemonize yes
        '';
      };
    };
    
    previews = {
      enable = true;
      previews = {
        frontend = {
          command = ["npm" "run" "dev" "--prefix" "frontend"];
          manager = "web";
          env = {
            PORT = "$PORT";
            NEXT_PUBLIC_API_URL = "https://$PORT-5000.preview.app.github.dev";
          };
        };
        backend = {
          command = ["./start-backend.sh"];
          manager = "web";
          env = {
            PORT = "5000";
            FLASK_ENV = "development";
          };
        };
      };
    };
  };
}