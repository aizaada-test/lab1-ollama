Common ports (reference for the security-tutor skill)
Port	Service	Note
21	FTP	Not encrypted, use SFTP instead
22	SSH	Secure remote login
23	Telnet	Not encrypted, should be disabled
25	SMTP	Sending email
53	DNS	Domain names to IP addresses
80	HTTP	Web, not encrypted
443	HTTPS	Web, encrypted with TLS
3306	MySQL	Database, should not be open to the internet
3389	RDP	Windows remote desktop, common attack target
