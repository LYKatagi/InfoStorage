from info_storage.main.app import main

if __name__ == "__main__":
    try: 
        main()
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")
        exit(0)
    finally:
        SystemExit(0)
