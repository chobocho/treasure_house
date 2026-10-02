// 슬라이드 p7-v6-roslyn-csc — C# 컴파일러는 .NET 어셈블리, C# 6.0
using System;
using System.Linq;
using System.Reflection;

class App
{
    const string Dir = "/usr/lib/dotnet/sdk/10.0.112/Roslyn/bincore/";

    static void Show(string file)
    {
        Assembly a = Assembly.LoadFrom(Dir + file);
        AssemblyName n = a.GetName();
        Console.WriteLine("{0} {1}", n.Name, n.Version);
        MethodInfo main = a.EntryPoint;
        if (main != null)
            Console.WriteLine("  Main: " + main.DeclaringType.FullName);
        Console.WriteLine("  public types: " +
            a.GetExportedTypes().Length);
        var refs = a.GetReferencedAssemblies()
            .Select(r => r.Name).Where(r => r.StartsWith("Microsoft"))
            .OrderBy(r => r);
        foreach (string r in refs)
            Console.WriteLine("  -> " + r);
    }

    static void Main()
    {
        Show("csc.dll");
        Show("Microsoft.CodeAnalysis.CSharp.dll");
        Show("Microsoft.CodeAnalysis.dll");
    }
}
