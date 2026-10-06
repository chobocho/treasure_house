// 슬라이드 p14-v13-pp-runtime — 생성기 특성이 속성에도 붙는다, C# 13.0
using System;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;

partial class Patterns
{
#if BAD
    // with no generator running, nobody writes the implementation
    [GeneratedRegex("a+")]
    private static partial Regex As { get; }
#endif
}

class App
{
    static void Show(Type t) => Console.WriteLine(t.Name + ": "
        + t.GetCustomAttribute<AttributeUsageAttribute>().ValidOn);

    static void Main()
    {
        Show(typeof(GeneratedRegexAttribute));
        Show(typeof(LibraryImportAttribute));
    }
}
