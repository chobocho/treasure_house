// 슬라이드 p12-v11-ck-runtime — Int128 과 BCL 의 checked, C# 11.0
using System;
using System.Linq;

class App
{
    static void Main()
    {
        Int128 max = Int128.MaxValue;
        Console.WriteLine(max);
        Console.WriteLine(unchecked(max + 1));
        try { Console.WriteLine(checked(max + 1)); }
        catch (OverflowException) { Console.WriteLine("Overflow"); }

        // Public types of CoreLib that declare a checked operator
        var names = typeof(object).Assembly.GetExportedTypes()
            .Where(t => !t.IsInterface && t.GetMethods()
                .Any(m => m.IsSpecialName && m.DeclaringType == t
                    && m.Name.StartsWith("op_Checked")))
            .Select(t => t.Name).OrderBy(s => s, StringComparer.Ordinal)
            .ToArray();
        Console.WriteLine(names.Length + " types:");
        for (int i = 0; i < names.Length; i += 8)
            Console.WriteLine("  " + string.Join(" ",
                names.Skip(i).Take(8)));
    }
}
