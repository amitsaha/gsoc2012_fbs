#version=DEVEL
repo --name="fedora" --mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=fedora-$releasever&arch=$basearch --excludepkgs="kernel*debug*,kernel-kdump*,syslog-ng*,java-1.5.0-gcj-devel,astronomy-bookmarks,generic*,java-1.5.0-gcj-javadoc,btanks*,GConf2-dbus*,bluez-gnome"
repo --name="fedora-source" --mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=fedora-source-$releasever&arch=$basearch --excludepkgs="kernel*debug*,kernel-kdump*,syslog-ng*,java-1.5.0-gcj-devel,astronomy-bookmarks,generic*,java-1.5.0-gcj-javadoc,btanks*,GConf2-dbus*,bluez-gnome"
# Installation logging level
logging --level=info


%packages --default

%end
