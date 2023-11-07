let
  sourcesTarball = fetchTarball "https://github.com/mutwo-org/mutwo-nix/archive/refs/heads/main.tar.gz";
  mutwo-timeline = import (sourcesTarball + "/mutwo.timeline/default.nix") {};
  mutwo-timeline-local = mutwo-timeline.overrideAttrs (
    finalAttrs: previousAttrs: {
       src = ./.;
    }
  );
in
  mutwo-timeline-local

