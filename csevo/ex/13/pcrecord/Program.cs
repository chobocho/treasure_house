// 슬라이드 p13-v12-pc-notprop — 같은 괄호, 다른 멤버, C# 12.0
using System;
using System.Linq;
using System.Reflection;

record PointR(int X, int Y);
class PointC(int X, int Y)
{
    public int Sum => X + Y;
}

class App
{
    static void List(Type t)
    {
        var flags = BindingFlags.Public | BindingFlags.NonPublic
                  | BindingFlags.Instance | BindingFlags.DeclaredOnly;
        foreach (var g in t.GetMembers(flags)
            .Where(m => m is FieldInfo or PropertyInfo
                || m is MethodInfo { IsSpecialName: false })
            .GroupBy(m => m.MemberType).OrderBy(x => x.Key))
            Console.WriteLine($"{t.Name} {g.Key,-8}: "
                + string.Join(" ", g.Select(m => m.Name)
                    .Order(StringComparer.Ordinal)));
    }

    static void Main()
    {
        List(typeof(PointR));
        List(typeof(PointC));
    }
}
