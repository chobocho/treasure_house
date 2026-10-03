// 슬라이드 p11-v10-implicit — SDK 의 암시적 using 목록, C# 10.0
using System;
using System.Linq;
using System.Xml.Linq;

class App
{
    const string Sdk = "/usr/lib/dotnet/sdk/10.0.112/Sdks/"
        + "Microsoft.NET.Sdk/targets/";

    static void Main()
    {
        var props = XDocument.Load(Sdk
            + "Microsoft.NET.Sdk.CSharp.props");
        foreach (var e in props.Descendants()
                     .Where(e => e.Name.LocalName == "Using"))
        {
            var cond = e.Attribute("Condition") == null ? "" : " (if)";
            Console.WriteLine("Using " + e.Attribute("Include").Value
                + cond);
        }
        var gen = XDocument.Load(Sdk
            + "Microsoft.NET.GenerateGlobalUsings.targets");
        var file = gen.Descendants()
            .First(e => e.Name.LocalName
                == "GeneratedGlobalUsingsFile");
        Console.WriteLine(file.Value);
    }
}
