// 슬라이드 p2-v1-indexername — 인덱서의 이름은 Item, C# 1.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

class Grid
{
    public int this[int r, int c] { get { return r * 10 + c; } }
}

class Sheet
{
    [IndexerName("Cell")]
    public int this[int r, int c] { get { return r * 100 + c; } }
}

class App
{
    static void Show(Type t)
    {
        Type dm = typeof(DefaultMemberAttribute);
        object[] a = t.GetCustomAttributes(dm, true);
        string member = ((DefaultMemberAttribute)a[0]).MemberName;
        PropertyInfo p = t.GetProperty(member);
        Console.WriteLine(t.Name + ": " + member + ", getter "
            + p.GetGetMethod().Name + ", "
            + p.GetIndexParameters().Length + " parameter(s)");
    }

    static void Main()
    {
        Show(typeof(Grid));
        Show(typeof(Sheet));
        Show(typeof(string));
        Show(typeof(System.Collections.ArrayList));
        Console.WriteLine(new Sheet()[2, 3]);
    }
}
