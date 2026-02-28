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
    };
}
