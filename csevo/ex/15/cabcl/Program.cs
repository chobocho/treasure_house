// 슬라이드 p15-v14-ca-bcl — .NET 10 참조 팩의 복합 대입 연산자, C# 14
using System;
using System.IO;
using System.Linq;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Runtime.InteropServices;

class Probe { public void operator +=(int d) { } }  // self-check

class Program
{
    // (types, op_Addition count, names ending in "Assignment")
    static (int, int, string[]) Scan(string[] files)
    {
        int types = 0, adds = 0;
        var hits = new System.Collections.Generic.List<string>();
        foreach (string f in files)
        {
            using var pe = new PEReader(File.OpenRead(f));
            MetadataReader md = pe.GetMetadataReader();
            foreach (var th in md.TypeDefinitions)
            {
                types++;
                var t = md.GetTypeDefinition(th);
                foreach (var mh in t.GetMethods())
                {
                    var m = md.GetMethodDefinition(mh);
                    string n = md.GetString(m.Name);
                    if (n == "op_Addition") adds++;
                    if (n.StartsWith("op_") && n.EndsWith("Assignment"))
                        hits.Add(md.GetString(t.Name) + "." + n);
                }
            }
        }
        hits.Sort(StringComparer.Ordinal);
        return (types, adds, hits.ToArray());
    }

    static void Main()
    {
        string dir = Path.Combine(RuntimeEnvironment
            .GetRuntimeDirectory(), "../../../packs",
            "Microsoft.NETCore.App.Ref", Environment.Version.ToString(),
            "ref/net10.0");
        var (t, a, h) = Scan(Directory.GetFiles(dir, "*.dll"));
        Console.WriteLine("ref pack: " + t + " types, " + a
            + " op_Addition, " + h.Length + " op_*Assignment");
        (t, a, h) = Scan([typeof(Program).Assembly.Location]);
        Console.WriteLine("this dll: " + string.Join(" ", h));
    }
}
