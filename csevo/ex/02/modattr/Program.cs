// 슬라이드 p2-v1-modattr — 특성 대상 module:, C# 1.0
using System;

[assembly: CLSCompliant(true)]           // assembly: target, C# 1
[module: CLSCompliant(true)]             // module: target

public class App
{
    public static void Main()
    {
        Type c = typeof(CLSCompliantAttribute);
        Console.WriteLine("assembly: "
            + typeof(App).Assembly.IsDefined(c, false));
        Console.WriteLine("module:   "
            + typeof(App).Module.IsDefined(c, false));
    }
}
