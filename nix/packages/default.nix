pkgs: rec {
  anifetch = pkgs.callPackage ./anifetch.nix { };
  default = anifetch;
}
