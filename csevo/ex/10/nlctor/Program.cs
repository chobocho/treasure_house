// 슬라이드 p10-v9-nl-ctor — 생성자의 nullable 분석, C# 9.0
using System;

public class C
{
    public string Prop { get; set; }

    public C()
    {
        Init();
        if (Prop is null)
            throw new InvalidOperationException();
    }

    void Init() => Prop = "some default";
}

public class D
{
    public string Prop { get; set; }

    public D()
    {
        Console.WriteLine(Prop.Length);   // read before any write
        Prop = "";
    }
}

class App
{
    static void Main() => Console.WriteLine(new C().Prop);
}
