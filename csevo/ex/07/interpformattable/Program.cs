// 슬라이드 p7-v6-interp-formattable — FormattableString, C# 6.0
using System;

class App
{
    static void Main()
    {
        string user = "ada";
        int id = 42;
        FormattableString f = $"user {user,-5} id {id:D4} {{x}}";

        Console.WriteLine("Format:        " + f.Format);
        Console.WriteLine("ArgumentCount: " + f.ArgumentCount);
        for (int i = 0; i < f.ArgumentCount; i++)
        {
            object a = f.GetArgument(i);
            Console.WriteLine("  arg {0}: {1} ({2})",
                i, a, a.GetType().Name);
        }
        Console.WriteLine("ToString():    " + f);
    }
}
