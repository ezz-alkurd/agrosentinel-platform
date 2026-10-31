# AgroSentinel public website

The website is edited directly in this folder. Open AgroSentinel.Presentation.sln in Microsoft Visual Studio, select AgroSentinel.Web, and press F5. The project targets ASP.NET Core 8 Razor Pages and opens http://localhost:5168.

## Main files

- Pages/Index.cshtml: public project content.
- wwwroot/css/site.css: white/charcoal layout with a forest-green accent.
- wwwroot/js/site.js: model accordion, pipeline, film tabs and mobile navigation.
- wwwroot/images/: locally stored, licensed agricultural photographs.
- wwwroot/fonts/: Manrope font and its SIL Open Font License.
- wwwroot/media/: both original user-supplied videos.
- docs/PHOTO-CREDITS.md: image sources and licensing information.

The public website has no presenter mode, speaker notes, rehearsal checklist, guide downloads, development-status panels, invented live measurements or model-accuracy figures. The previous guide has been moved outside wwwroot, and its former public URL explicitly returns 404.

All photographs and fonts are served locally. Browsing does not require external image or font hosts. The drone MP4 is unchanged. The rover-web.mp4 playback copy moves MP4 metadata to the beginning without changing audio/video payloads. The original rover.mp4 remains locally and is excluded from new publish output.

The photographs show representative agricultural scenes and third-party equipment. They are not evidence that the pictured machines were built by the project team. Required robot-image attribution is included in the footer.

## Publishing to SmarterASP

Right-click the project, select Publish, choose the SmarterASP folder profile and publish. Upload the contents of bin/Release/net8.0/publish to an ASP.NET Core 8-capable SmarterASP website root. Include web.config and wwwroot. The profile creates a folder and does not upload to an account.

Command-line alternatives:

    dotnet run --project AgroSentinel.Presentation.csproj --launch-profile AgroSentinel.Web
    dotnet build AgroSentinel.Presentation.sln -c Release
    dotnet publish -c Release -p:PublishProfile=SmarterASP

The integrated control API requires NuGet packages for SQL Server and Firebase token validation. NuGet.org is configured in NuGet.Config. Install the .NET 8 SDK including its targeting packs before an offline build. The local laptop launcher can also run the compiled site when the ASP.NET Core 8 runtime is installed.

## Project boundaries

This website explains the project and its architecture. AI-model hosting, mobile-app UI cleanup, APK generation, the detector runtime and hardware integration are separate work. The public model sections describe their intended roles without claiming a new close-up/far training release.

The public presentation pages need no sign-in. The integrated /api/v1 backend requires private SQL Server and evidence settings; see ../docs/SMARTERASP_SETUP.md. Model inference stays on the laptop.
