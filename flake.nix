{
  description = "A simple CLI for updating a nixos config for people who use my config and want to fetch updates easily";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      packages.${system}.default =
        pkgs.python3Packages.buildPythonApplication {
          pname = "nixos-update";
          version = "0.0.1";

          src = ./.;
          format = "other";

          propagatedBuildInputs = with pkgs.python313Packages; [
            platformdirs
            pygithub
          ];

          installPhase = ''
            mkdir -p $out/bin
            install -m755 nixos-update.py $out/bin/nixos-update
          ''; 
        };

      nixosModules.default = { config, lib, pkgs, ... }:
        let
          cfg = config.programs.nixos-update;
        in { 
          options.programs.nixos-update = {
            enable = lib.mkEnableOption "Nixos update";

            settings = lib.mkOption {
              type = lib.types.attrs;
              default = {
                githubRepo = "";
                access_token = "";
                hostname = "${config.networking.hostName}";
              };

              description = "nixos update JSON config";
            };

          };

          config = lib.mkIf cfg.enable {
            environment.systemPackages = [ self.packages.${system}.default ];

            environment.etc."nixos-update/settings.json".text =
              builtins.toJSON cfg.settings;
          };
        };
    };
}
