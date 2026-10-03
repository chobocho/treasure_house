// 슬라이드 p12-v11-rq-null — required 와 nullable 경고, C# 11
using System;

#if OLD
class Old { public string Name { get; set; } }             // CS8618
#endif
class Bang { public string Name { get; set; } = null!; }   // C# 8 way
class New { public required string Name { get; set; } }

class Program
{
    static void Main()
    {
        var a = new Bang();                // compiles, Name is null
        Console.WriteLine(a.Name is null);
        var b = new New { Name = "set" };
        Console.WriteLine(b.Name.Length);
#if BAD
        var c = new New { Name = null };   // still a nullable warning
#endif
    }
}
