// 슬라이드 p7-v6-roslyn-api — 구문 트리를 돌려주는 API, C# 6.0
using System;
using System.Reflection;

class App
{
    const string Dir = "/usr/lib/dotnet/sdk/10.0.112/Roslyn/bincore/";

    // walk the tree: node type, then its source text
    static void Dump(dynamic node, int depth)
    {
        string kind = ((object)node).GetType().Name;
        kind = kind.Replace("Syntax", "");
        Console.WriteLine("{0}{1,-30} {2}",
            new string(' ', depth * 2), kind, node.ToString());
        foreach (dynamic child in node.ChildNodes())
            Dump(child, depth + 1);
    }

    static void Main()
    {
        Assembly cs = Assembly.LoadFrom(
            Dir + "Microsoft.CodeAnalysis.CSharp.dll");
        MethodInfo parse = cs
            .GetType("Microsoft.CodeAnalysis.CSharp.SyntaxFactory")
            .GetMethod("ParseExpression");
        string text = "$\"{nameof(p)}={p?.Name,-5}\"";
        object tree = parse.Invoke(null,
            new object[] { text, 0, null, true });
        Dump(tree, 0);
    }
}
