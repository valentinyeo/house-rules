# Install the inne rules copy

Run on Hetzner from this repository:

```sh
sudo bash bin/install-inne.sh
sudo python3 /opt/house-rules-inne/bin/test-inne-sync.py
```

Updates run every five minutes.
Downloads use valentin's existing access.
The private source stays inaccessible to inne.
The shared copy contains filtered rules.
Its skill reads only local files.
Secret patterns block updates, preserving the previous copy.

Daily skill updates restore the house-rules link.
No new credentials reach inne.

To stop updates while keeping the last copy:

```sh
sudo systemctl disable --now house-rules-inne.timer
```
