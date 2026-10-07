// 슬라이드 p15-v14-pe-meta — 두 조각의 특성은 합쳐진다, C# 14
using System;
using System.Linq;
using System.Reflection;

[AttributeUsage(AttributeTargets.All, AllowMultiple = true)]
class TagAttribute(string s) : Attribute
{
    public override string ToString() => s;
}

partial class Job
{
    [Tag("def")] public partial Job(int id);
    [Tag("def")] public partial event Action Done;
}

partial class Job
{
    [Tag("impl")] public partial Job(int id) { }
    [Tag("impl")] public partial event Action Done
    {
        [Tag("add")] add { }
        remove { }
    }
}

class Program
{
    static string Tags(MemberInfo m) =>
        string.Join(" ", m.GetCustomAttributes<TagAttribute>());

    static void Main()
    {
        var t = typeof(Job);
        Console.WriteLine("ctors: " + t.GetConstructors().Length);
        Console.WriteLine("ctor:  " + Tags(t.GetConstructors()[0]));
        var e = t.GetEvent("Done");
        Console.WriteLine("event: " + Tags(e));
        Console.WriteLine("add:   " + Tags(e.AddMethod));
        Console.WriteLine("fields: " + t.GetFields(
            BindingFlags.NonPublic | BindingFlags.Instance).Length);
    }
}
