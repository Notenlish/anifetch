{
  description = "Neofetch but animated";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    git-hooks.url = "github:cachix/git-hooks.nix";
  };

  outputs =
    {
      self,
      nixpkgs,
      ...
    }:
    let
      inherit (self) inputs;
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.callPackage ./nix/package.nix { };
          anifetch = self.packages.${system}.default;
        }
      );

      overlays = {
        default = final: _prev: {
          anifetch = import ./nix/package.nix final.pkgs;
        };
        anifetch = self.overlays.default;
      };

      formatter = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          config = self.checks.${system}.pre-commit-check.config;
          inherit (config) package configFile;
          script = ''
            ${pkgs.lib.getExe package} run --all-files --config ${configFile}
          '';
        in
        pkgs.writeShellScriptBin "pre-commit-run" script
      );

      checks = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          pre-commit-check = inputs.git-hooks.lib.${system}.run {
            src = ./.;
            hooks = {
              nixfmt.enable = true;

              ruff-check = {
                enable = true;
                entry = "${pkgs.lib.getExe pkgs.ruff}";
                args = [
                  "check"
                  "--fix"
                ];
                types = [
                  "file"
                  "python"
                ];
              };
              ruff-format = {
                enable = true;
                entry = "${pkgs.lib.getExe pkgs.ruff}";
                args = [
                  "format"
                ];
                types = [
                  "file"
                  "python"
                ];
              };
            };

            package = pkgs.prek;
          };
        }
      );

      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          inherit (self.checks.${system}.pre-commit-check) shellHook enabledPackages;
        in
        {
          default = pkgs.mkShell {
            inherit shellHook;
            nativeBuildInputs = [
              self.packages.${system}.default
            ]
            ++ enabledPackages;
          };
        }
      );
    };
}
