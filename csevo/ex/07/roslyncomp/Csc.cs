// 슬라이드 p7-v6-roslyn-comp — 프로그램 안의 컴파일러(도우미), C# 6.0
using System;
using System.Reflection;
using System.Text;
using System.Threading;

static class Csc
{
    const string Dir = "/usr/lib/dotnet/sdk/10.0.112/Roslyn/bincore/";
    const string NS = "Microsoft.CodeAnalysis.";
    static Assembly core = Assembly.LoadFrom(Dir + NS + "dll");
    static Assembly cs = Assembly.LoadFrom(Dir + NS + "CSharp.dll");

    // CSharpSyntaxTree.ParseText at a language version
    static object Parse(string text, string version)
    {
        Type lv = cs.GetType(NS + "CSharp.LanguageVersion");
        Type po = cs.GetType(NS + "CSharp.CSharpParseOptions");
        dynamic opts = po.GetProperty("Default").GetValue(null);
        opts = opts.WithLanguageVersion(
            (dynamic)Enum.Parse(lv, version));
        MethodInfo m = cs.GetType(NS + "CSharp.CSharpSyntaxTree")
            .GetMethod("ParseText", new[] { typeof(string), po,
                typeof(string), typeof(Encoding),
                typeof(CancellationToken) });
        return m.Invoke(null, new object[] { text, opts, "a.cs", null,
            CancellationToken.None });
    }

    // CSharpCompilation.Create("a", [tree], [corelib])
    public static dynamic Compile(string text, string version)
    {
        Type st = core.GetType(NS + "SyntaxTree");
        Array trees = Array.CreateInstance(st, 1);
        trees.SetValue(Parse(text, version), 0);
        Type mr = core.GetType(NS + "MetadataReference");
        Array refs = Array.CreateInstance(mr, 1);
        string corelib = typeof(object).Assembly.Location;
        refs.SetValue(mr.GetMethod("CreateFromFile").Invoke(null,
            new object[] { corelib, null, null }), 0);
        return cs.GetType(NS + "CSharp.CSharpCompilation")
            .GetMethod("Create")
            .Invoke(null, new object[] { "a", trees, refs, null });
    }
}
