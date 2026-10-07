// 슬라이드 p16-st-lang-lib — 컴파일러가 끌어오는 라이브러리 형식, C# 14
using System;
using System.IO;
using System.Linq;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Threading.Tasks;

class Program
{
    static async Task Main()
    {
        int[] a = { 1, 2, 3, 4 };
        var pair = (a[^1], a[1..].Length);    // tuple, index, range
        await Task.Yield();                   // async state machine
        Console.WriteLine($"{pair.Item1} {pair.Item2}");
        foreach (string n in TypeRefs()) Console.WriteLine("  " + n);
    }

    // namespaces of the reader below - not what the compiler adds
    static readonly string[] Skip = { "System.IO", "System.Linq",
        "System.Reflection.Metadata",
        "System.Reflection.PortableExecutable" };

    // every type this assembly refers to, read from its own metadata
    static string[] TypeRefs()
    {
        string path = typeof(Program).Assembly.Location;
        using var pe = new PEReader(File.OpenRead(path));
        MetadataReader md = pe.GetMetadataReader();
        return md.TypeReferences
            .Select(h => md.GetTypeReference(h))
            .Select(t => md.GetString(t.Namespace) + "."
                       + md.GetString(t.Name))
            .Where(n => !Skip.Contains(n[..n.LastIndexOf('.')]))
            .OrderBy(s => s, StringComparer.Ordinal)
            .ToArray();
    }
}
