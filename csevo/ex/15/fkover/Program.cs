// 슬라이드 p15-v14-fk-over — override 속성의 field, C# 14
using System;
using System.Reflection;

class Base
{
    public virtual int N { get; set; } = 1;
}

class Derived : Base
{
    public override int N { get => field; set => field = value * 10; }
    public int BaseN => base.N;
}
#if HALF
class Half : Base
{
    public override int N { get => field + 1; }
}
#endif

class Program
{
    static void Main()
    {
        Base b = new Derived();
        b.N = 5;
        Console.WriteLine(b.N + " " + ((Derived)b).BaseN);
        var flags = BindingFlags.NonPublic | BindingFlags.Instance
            | BindingFlags.DeclaredOnly;
        foreach (var t in new[] { typeof(Base), typeof(Derived) })
            foreach (var f in t.GetFields(flags))
                Console.WriteLine(t.Name + ": " + f.Name);
    }
}
