# frozen_string_literal: true

# Keep jekyll-sitemap's URL generation while simplifying only the root element.
module SitemapHeaderPatch
  XSI_NAMESPACE_ATTRIBUTE =
    /\s+xmlns:xsi=(["'])http:\/\/www\.w3\.org\/2001\/XMLSchema-instance\1/
  SCHEMA_LOCATION_ATTRIBUTE =
    /\s+xsi:schemaLocation=(["'])http:\/\/www\.sitemaps\.org\/schemas\/sitemap\/0\.9\s+http:\/\/www\.sitemaps\.org\/schemas\/sitemap\/0\.9\/sitemap\.xsd\1/

  def self.rewrite(output)
    output
      .gsub(XSI_NAMESPACE_ATTRIBUTE, "")
      .gsub(SCHEMA_LOCATION_ATTRIBUTE, "")
  end
end

Jekyll::Hooks.register :pages, :post_render do |page|
  next unless page.url == "/sitemap.xml"

  page.output = SitemapHeaderPatch.rewrite(page.output)
end
