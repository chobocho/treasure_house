// 슬라이드 p12-v11-raw-const — 원시 문자열은 그냥 상수다, C# 11.0
using System;
using System.ComponentModel;

class App
{
    const string Name = """Ada "the first" """;
    const string Greeting = $"""Hello, {Name}!""";   // const interp

    [Description("""say "hi" """)]
    static void Hi() { }

    static string Kind(string s) => s switch
    {
        """a\b""" => "backslash",
        """
        two
        lines
        """ => "two lines",
        _ => "other",
    };

    static void Main()
    {
        Console.WriteLine(Greeting);
        Console.WriteLine(Kind("a\\b") + ", " + Kind("two\nlines"));
        Console.WriteLine(ReferenceEquals("""a\b""", @"a\b"));
        var d = (DescriptionAttribute)Attribute.GetCustomAttribute(
            typeof(App).GetMethod("Hi",
                System.Reflection.BindingFlags.Static
                | System.Reflection.BindingFlags.NonPublic),
            typeof(DescriptionAttribute));
        Console.WriteLine(d.Description);
    }
}
