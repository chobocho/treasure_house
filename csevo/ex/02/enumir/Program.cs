// 슬라이드 p2-v1-enumir — 열거형은 value__ 필드 하나, C# 1.0
using System;
using System.Reflection;

enum Size : byte { Small = 1, Medium, Large = 10 }

class App
{
    static void Main()
    {
        BindingFlags all = BindingFlags.Public | BindingFlags.NonPublic
            | BindingFlags.Static | BindingFlags.Instance;
        FieldInfo[] fs = typeof(Size).GetFields(all);
        for (int i = 0; i < fs.Length; i++)
        {
            FieldInfo f = fs[i];
            string kind = f.IsLiteral ? "const " : "field ";
            object v = f.IsLiteral ? f.GetRawConstantValue() : "-";
            Console.WriteLine(kind + f.FieldType.Name + " " + f.Name
                + " = " + v);
        }
        Console.WriteLine(typeof(Size).IsValueType);
        Console.WriteLine(typeof(Size).IsSealed);
    }
}
