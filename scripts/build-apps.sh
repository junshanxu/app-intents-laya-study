#!/bin/zsh
set -euo pipefail
project_dir=${0:A:h:h}
team=${APPLE_DEVELOPMENT_TEAM:-}
if [[ -z "$team" ]]; then
  print -u2 'Set APPLE_DEVELOPMENT_TEAM to a Personal Team or Apple Developer team ID.'
  exit 2
fi
cd "$project_dir"
xcodegen generate --spec project.yml
for scheme in TripLedger TaskBoard; do
  xcodebuild -project AppIntentsLayaStudy.xcodeproj -scheme "$scheme" \
    -configuration Debug -derivedDataPath .build \
    DEVELOPMENT_TEAM="$team" CODE_SIGNING_ALLOWED=YES CODE_SIGN_STYLE=Automatic build -quiet
  source_app="$project_dir/.build/Build/Products/Debug/$scheme.app"
  signature=$(codesign -dv --verbose=4 "$source_app" 2>&1)
  if [[ "$signature" == *'Signature=adhoc'* || "$signature" == *'TeamIdentifier=not set'* ]]; then
    print -u2 "$scheme was not signed with a validated development identity"
    exit 3
  fi
  destination="$HOME/Applications/AppIntentsLayaStudy/$scheme.app"
  mkdir -p "${destination:h}"
  ditto "$source_app" "$destination"
  /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$destination"
  print "Installed signed $destination"
done
