// 슬라이드 p15-v14-fk-nullset — setter 는 작은 생성자, C# 14
using System;

class C
{
    string Prop
    {
        get => field;
#if PARTIAL
        set { if (value.Length > 1) field = value; }
#else
        set { }           // never writes the backing field
#endif
    }

    public C()
    {
        Prop = "a";       // ok for the constructor analysis
    }

    public static void Main()
    {
        try { Console.WriteLine(new C().Prop.Length); }
        catch (NullReferenceException) { Console.WriteLine("NRE"); }
    }
}
