import os
import sys
import argparse
import shutil

# Bu komut satırı arayüzü, projenin en üst seviye CLI aracıdır.
# bead create, bead dev gibi komutları içerir.

def create_project(project_name):
    """
    Yeni bir Bead projesi oluşturur.
    """
    current_dir = os.getcwd()
    project_path = os.path.join(current_dir, project_name)

    if os.path.exists(project_path):
        print(f"Hata: '{project_name}' adında bir klasör zaten var.")
        return

    print(f"'{project_name}' projesi oluşturuluyor...")
    
    # Proje klasörlerini oluştur
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, "pages"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "components"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "public"), exist_ok=True)

    # Temel proje dosyalarını oluştur
    with open(os.path.join(project_path, "app.py"), "w", encoding="utf-8") as f:
        f.write("# Bead uygulaması ana dosyası")

    with open(os.path.join(project_path, "bead.config.json"), "w", encoding="utf-8") as f:
        f.write('{\n  "server": { "port": 3000 }\n}')
        
    with open(os.path.join(project_path, "pages", "index.bead"), "w", encoding="utf-8") as f:
        f.write("""from bead.ui import Page, Text
def default(params, context):
    return Page(title="Ana Sayfa", body=[Text("Merhaba, Bead!")])
""")

    # Geliştirici deneyimini kolaylaştırmak için run.py ve requirements.txt oluştur
    # Bu dosyalar, kullanıcının projeyi direkt çalıştırmasını sağlar.
    with open(os.path.join(project_path, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write("# Bead framework'ü için gerekli bağımlılıkları içerir.\n")
        f.write("uvicorn\n")
        f.write("starlette\n")
        f.write("-e ../bead\n")
    
    with open(os.path.join(project_path, "run.py"), "w", encoding="utf-8") as f:
        f.write("import os\n")
        f.write("import sys\n")
        f.write("\n")
        f.write("script_dir = os.path.dirname(os.path.abspath(__file__))\n")
        f.write("parent_dir = os.path.dirname(script_dir)\n")
        f.write("sys.path.insert(0, parent_dir)\n")
        f.write("\n")
        f.write("import bead.cli\n")
        f.write("if __name__ == '__main__':\n")
        f.write("    sys.argv = ['bead', 'dev', '.']\n")
        f.write("    bead.cli.main()\n")

    print(f"'{project_name}' projesi başarıyla oluşturuldu!")
    print("--------------------------------------------------")
    print(f"Projenizi çalıştırmak için:")
    print(f"1. 'cd {project_name}' komutuyla proje dizinine gidin.")
    print(f"2. 'pip install -r requirements.txt' komutunu çalıştırın.")
    print(f"3. 'python run.py' komutuyla sunucuyu başlatın.")
    print("--------------------------------------------------")


def main():
    """
    CLI giriş noktası.
    """
    parser = argparse.ArgumentParser(description="Bead Framework CLI")
    
    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser("create", help="Yeni bir Bead projesi oluşturur.")
    create_parser.add_argument("project_name", help="Oluşturulacak projenin adı.")
    
    # `bead dev` komutu artık proje klasörünü argüman olarak alır
    dev_parser = subparsers.add_parser("dev", help="Geliştirme sunucusunu başlatır.")
    dev_parser.add_argument("project_path", nargs="?", default=".", help="Proje dizininin yolu.")

    args = parser.parse_args()
    
    # Eğer `start_dev_server` fonksiyonu daha önce import edilmediyse
    # Bu import'u burada yaparak, dev komutunun çalışacağı klasörü doğru bir şekilde belirlemesini sağlıyoruz
    from bead.server.dev_server import start_dev_server

    if args.command == "create":
        create_project(args.project_name)
    elif args.command == "dev":
        start_dev_server(os.path.abspath(args.project_path))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()