#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Inicialização Completa - Rota Verde
Prepara e executa todo o sistema de segurança
"""

import subprocess
import sys
import os
import time


def print_header():
    """Exibe cabeçalho do sistema"""
    print("=" * 60)
    print("🏦 ROTA VERDE - SISTEMA DE SEGURANÇA")
    print("   Gestão de Fluxo de Caixa Protegido")
    print("=" * 60)


def check_dependencies():
    """Verifica e instala dependências necessárias"""
    print("\n📦 Verificando dependências...")
    
    required_packages = [
        "streamlit",
        "pandas", 
        "plotly",
        "openpyxl",
        "python-dateutil"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (faltando)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📥 Instalando {len(missing_packages)} pacote(s) faltando(s)...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages)
            print("✅ Todas as dependências instaladas com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar dependências: {e}")
            return False
    else:
        print("✅ Todas as dependências estão instaladas!")
    
    return True


def compile_security_validator():
    """Compila o validador de segurança"""
    print("\n🔐 Compilando validador de segurança...")
    
    if os.path.exists("password_validator.exe"):
        print("  ✅ Validador já compilado encontrado!")
        return True
    
    if not os.path.exists("auth_validator.py"):
        print("  ❌ Arquivo fonte do validador não encontrado!")
        return False
    
    try:
        # Tenta compilar se PyInstaller estiver disponível
        result = subprocess.run(
            ["python", "compile_validator.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("  ✅ Validador compilado com sucesso!")
            return True
        else:
            print("  ⚠️ Compilação não disponível, usando validador Python")
            return True
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("  ⚠️ PyInstaller não disponível, usando validador Python")
        return True
    except Exception as e:
        print(f"  ⚠️ Erro na compilação: {e}")
        return True  # Continua mesmo sem compilar


def test_authentication():
    """Testa o sistema de autenticação"""
    print("\n🧪 Testando sistema de autenticação...")
    
    try:
        # Importa o validador
        from auth_validator import PasswordValidator
        
        validator = PasswordValidator()
        
        # Testa senha válida
        success, message, _ = validator.validate_password("RotaVerde2024")
        if success:
            print("  ✅ Autenticação funcionando corretamente!")
            return True
        else:
            print(f"  ❌ Problema na autenticação: {message}")
            return False
            
    except ImportError:
        print("  ❌ Não foi possível importar o validador!")
        return False
    except Exception as e:
        print(f"  ❌ Erro no teste de autenticação: {e}")
        return False


def show_security_info():
    """Mostra informações de segurança"""
    print("\n🔑 INFORMAÇÕES DE ACESSO:")
    print("-" * 30)
    print("📋 Senhas Padrão:")
    print("  • Admin: RotaVerde2024")
    print("  • User:  FluxoCaixa@2024")
    print()
    print("🛡️ Recursos de Segurança:")
    print("  • Controle de tentativas (máx. 3)")
    print("  • Bloqueio temporário (5 minutos)")
    print("  • Hash SHA-256 com salt")
    print("  • Sessão segura durante uso")
    print()
    print("⚠️ IMPORTANTE:")
    print("  • Não compartilhe as senhas")
    print("  • Faça logout ao terminar")
    print("  • Troque as senhas em produção")


def start_application():
    """Inicia a aplicação principal"""
    print("\n🚀 Iniciando aplicação...")
    print("📱 Abrindo Streamlit no navegador...")
    print("🌐 URL: http://localhost:8501")
    print()
    print("💡 Para parar o servidor: Ctrl+C no terminal")
    print("🔄 Para reiniciar: Execute este script novamente")
    print()
    print("=" * 60)
    
    try:
        # Inicia o Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "true",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor interrompido pelo usuário")
        print("✅ Aplicação encerrada com segurança")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar aplicação: {e}")


def main():
    """Função principal"""
    print_header()
    
    # Verifica se estamos no diretório correto
    if not os.path.exists("app.py"):
        print("\n❌ Erro: Execute este script na pasta do projeto!")
        print("📁 Certifique-se de estar na pasta 'Rota Verde'")
        input("\nPressione Enter para sair...")
        return
    
    # Executa verificações e preparação
    steps = [
        ("Verificar dependências", check_dependencies),
        ("Compilar validador", compile_security_validator),
        ("Testar autenticação", test_authentication)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        if not step_func():
            print(f"\n❌ Falha em: {step_name}")
            response = input("\n❓ Continuar mesmo assim? (s/N): ").strip().lower()
            if response not in ['s', 'sim', 'y', 'yes']:
                print("🛑 Inicialização cancelada")
                return
    
    # Mostra informações de segurança
    show_security_info()
    
    # Pergunta se quer iniciar
    print("\n" + "=" * 60)
    response = input("🚀 Iniciar aplicação agora? (S/n): ").strip().lower()
    
    if response in ['', 's', 'sim', 'y', 'yes']:
        start_application()
    else:
        print("\n✅ Sistema preparado!")
        print("💡 Para iniciar manualmente: streamlit run app.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        print("🔧 Tente executar manualmente: streamlit run app.py")
    finally:
        input("\nPressione Enter para sair...")