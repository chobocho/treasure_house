// 슬라이드 p8-v7_1-runtime — 이 덱이 컴파일할 때 쓰는 참조 팩, C# 7.1
using System;
using System.IO;
using System.Linq;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;

class App
{
    static void Dump(string label, string path)
    {
        var pe = new PEReader(File.OpenRead(path));
        MetadataReader md = pe.GetMetadataReader();
        int bodies = 0, throwNull = 0, ret = 0, ctor = 0;
        foreach (var h in md.MethodDefinitions)
        {
            MethodDefinition m = md.GetMethodDefinition(h);
            if (m.RelativeVirtualAddress == 0) continue;  // abstract
            bodies++;
            byte[] il = pe.GetMethodBody(m.RelativeVirtualAddress)
                .GetILBytes();
            if (il.SequenceEqual(new byte[] { 0x14, 0x7A }))
                throwNull++;                     // ldnull; throw
            else if (il.Length == 1 && il[0] == 0x2A)
                ret++;                           // ret
            else if (md.GetString(m.Name) == ".ctor")
                ctor++;
        }
        Console.WriteLine("{0}\n  types={1} forwarded={2} bodies={3}"
            + " throw-null={4} ret={5} other-ctor={6}", label,
            md.TypeDefinitions.Count, md.ExportedTypes.Count,
            bodies, throwNull, ret, ctor);
    }

    static void Main()
    {
        string pack = Directory.GetDirectories(
            "/usr/lib/dotnet/packs/Microsoft.NETCore.App.Ref").Max();
        string rt = Path.GetDirectoryName(
            typeof(object).Assembly.Location);
        Dump("ref pack: System.Runtime.dll",
            Path.Combine(pack, "ref", "net10.0", "System.Runtime.dll"));
        Dump("runtime: System.Runtime.dll",
            Path.Combine(rt, "System.Runtime.dll"));
        Dump("runtime: System.Private.CoreLib.dll",
            typeof(object).Assembly.Location);
    }
}
