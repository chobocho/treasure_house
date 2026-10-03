// 슬라이드 p12-v11-mgcache — 정적 메서드 그룹 대리자의 캐시, C# 11.0
using System;
using System.Reflection;

class App
{
    static int Twice(int x) => x * 2;

    static void Main()
    {
        Func<int, int> a = Twice;
        Func<int, int> b = Twice;
        Console.WriteLine("same object: " + ReferenceEquals(a, b));

        const BindingFlags All = BindingFlags.Static
            | BindingFlags.NonPublic | BindingFlags.Public;
        foreach (Type n in typeof(App).GetNestedTypes(All))
        {
            Console.WriteLine("nested " + n.Name);
            foreach (FieldInfo f in n.GetFields(All))
                Console.WriteLine($"  {f.Name} : {f.FieldType.Name}");
        }
    }
}
