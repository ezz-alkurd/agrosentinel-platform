using AgroSentinel.ControlApi;
using Microsoft.AspNetCore.StaticFiles;
using Microsoft.AspNetCore.DataProtection;
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddRazorPages();
builder.Services.AddAgroSentinelApi(builder.Configuration);
builder.Services.AddDataProtection().UseEphemeralDataProtectionProvider();
var app = builder.Build();
// The presentation handler must wrap API middleware, so API failures keep their JSON responses.
if (!app.Environment.IsDevelopment()) app.UseExceptionHandler("/Error");
app.MapAgroSentinelApi();
app.Use(async (context, next) =>
{
    // Keep the retired presentation handout private, including on older deployments.
    if (context.Request.Path.Equals("/presenter-guide.md", StringComparison.OrdinalIgnoreCase))
    {
        context.Response.StatusCode = StatusCodes.Status404NotFound;
        return;
    }
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    context.Response.Headers["Referrer-Policy"] = "strict-origin-when-cross-origin";
    context.Response.Headers["X-Frame-Options"] = "SAMEORIGIN";
    context.Response.Headers["Content-Security-Policy"] =
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'";
    await next();
});
var contentTypes = new FileExtensionContentTypeProvider();
contentTypes.Mappings[".webmanifest"] = "application/manifest+json";
app.UseStaticFiles(new StaticFileOptions { ContentTypeProvider = contentTypes });
app.MapRazorPages();
app.MapGet("/health", () => Results.Ok(new { status = "ok", service = "AgroSentinel presentation" }));
if (args.Contains("--verify"))
{
    app.Urls.Clear();
    app.Urls.Add("http://127.0.0.1:5179");
    await app.StartAsync();
    try
    {
        using var http = new HttpClient { BaseAddress = new Uri("http://127.0.0.1:5179"), Timeout = TimeSpan.FromSeconds(8) };
        var home = await http.GetAsync("/");
        home.EnsureSuccessStatusCode();
        var html = await home.Content.ReadAsStringAsync();
        if (!html.Contains("Know your field.") || html.Contains("asp-append-version")) throw new Exception("Razor page did not render.");
        if (html.Contains("data-notes") || html.Contains("presenter-guide") || html.Contains("data-start-presentation"))
            throw new Exception("Retired presenter content is still present.");
        if (!html.Contains("ONE CONNECTED FIELD") || html.Contains("class=\"hero-photograph\"><img src=\"/images/drone-photo.jpg\"")) throw new Exception("Hardware-neutral hero is missing.");
        Console.WriteLine("PASS: rendered public Razor page without presenter content");
        foreach (var path in new[] { "/health", "/css/site.css", "/js/site.js", "/images/drone-photo.jpg", "/images/rover-photo.jpg", "/images/field-photo.jpg", "/images/leaf-photo.jpg", "/images/fire-photo.jpg", "/images/fixed-camera-photo.jpg", "/images/phone-camera-photo.jpg", "/images/usb-camera-photo.webp", "/images/agrosentinel-logo.png", "/favicon.ico", "/icons/favicon-32.png", "/icons/apple-touch-icon.png", "/site.webmanifest", "/fonts/manrope.ttf" })
        {
            using var response = await http.GetAsync(path);
            response.EnsureSuccessStatusCode();
            Console.WriteLine("PASS: " + path);
        }
        foreach (var path in new[] { "/media/drone.mp4", "/media/rover-web.mp4" })
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, path);
            request.Headers.Range = new System.Net.Http.Headers.RangeHeaderValue(0, 1023);
            using var response = await http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead);
            if (response.StatusCode != System.Net.HttpStatusCode.PartialContent || response.Content.Headers.ContentLength != 1024)
                throw new Exception("Video range check failed: " + path);
            Console.WriteLine("PASS: video range " + path);
        }
        foreach (var path in new[] { "/not-a-real-page", "/presenter-guide.md", "/docs/presenter-guide.md" })
        {
            using var missing = await http.GetAsync(path);
            if (missing.StatusCode != System.Net.HttpStatusCode.NotFound) throw new Exception("Private/missing route is accessible: " + path);
            Console.WriteLine("PASS: unavailable public route " + path);
        }
    }
    finally { await app.StopAsync(); }
}
else await app.RunAsync();
