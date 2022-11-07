with import <nixpkgs> {};
with pkgs.python310Packages;

let

  mutwo-core-archive = builtins.fetchTarball "https://github.com/mutwo-org/mutwo.core/archive/61ebb657ef5806eb067f5df6885254fdbae8f44c.tar.gz";
  mutwo-core = import (mutwo-core-archive + "/default.nix");

  python-ranges = pkgs.python310Packages.buildPythonPackage rec {
    name = "python-ranges";
    src = fetchFromGitHub {
      owner = "Superbird11";
      repo = "ranges";
      rev = "38ac789b61e1e33d1a8be999ca969f909bb652c0";
      sha256 = "sha256-oRQCtDBQnViNP6sJZU0NqFWkn2YpcIeGWmfx3Ne/n2c=";
    };
    # TypeError: calling <class 'ranges.RangeDict.RangeDict'> returned {}, not a test
    doCheck = false;
    checkInputs = [ python310Packages.pytest ];
  };

in

  buildPythonPackage rec {
    name = "mutwo.timeline";
    src = fetchFromGitHub {
      owner = "mutwo-org";
      repo = name;
      rev = "f29956e8c410ee863bac268a32448dc66a9b2323";
      sha256 = "sha256-JXmawOBjC7vS29hAhvKKTssOql6czQfAaYgViGg0j6g=";
    };
    checkInputs = [
      python310Packages.pytest
    ];
    propagatedBuildInputs = [ 
      python310Packages.numpy
      mutwo-core
      python-ranges
    ];
    checkPhase = ''
      runHook preCheck
      pytest
      runHook postCheck
    '';
    doCheck = true;
  }
