
Have you ever run `vagrant global-status` and got no results even though you _know_ that there are VMs created by a vagrant environment on your machine?

Vagrant's documentation says that the only way to fix the problem is to destroy and recreate your VMs, but if you have a bunch, this is time consuming and probably a pain, especially if you have special VMs that you really can't destroy without a ton of extra work.

Clone this repo, run `./rebuild-machine-index` and you'll be good to go.
