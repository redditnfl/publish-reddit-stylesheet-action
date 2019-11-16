# publish-reddit-stylesheet-action

Github action for publishing a reddit stylesheet

# Usage

You need to setup an authenticated OAuth reddit client with modconfig scope

See [action.yml](action.yml)

```yaml
steps:
- uses: actions/checkout@master

# ...

# Take data from a previous step/job
- name: Download theme data
  uses: actions/download-artifact@v1.0.0
  with:
	name: themeartifact
	path: theme

# Deploy
- name: Deploy to my subreddit
  uses: redditnfl/publish-reddit-stylesheet-action@v1.0.0
  with:
	subreddit: mysubreddit
	path: theme
  env:
	praw_client_id: ${{ secrets.style_publisher_praw_client_id }}
	praw_client_secret: ${{ secrets.style_publisher_praw_client_secret }}
	praw_refresh_token: ${{ secrets.style_publisher_praw_refresh_token }}
```

# License

The scripts and documentation in this project are released under the [MIT License](LICENSE)
