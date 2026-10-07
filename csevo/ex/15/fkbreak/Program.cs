// 슬라이드 p15-v14-fk-break — field 라는 멤버를 쓰던 코드, C# 13
using System;

class Legacy
{
    int field;                    // old code: a member named field

    public int Value
    {
#if FIX
        get { return this.field; }
        set { @field = value; }
#else
        get { return field; }
        set { field = value; }
#endif
    }

    public int Raw() => field;         // a method: always the member
}

class Program
{
    static void Main()
    {
        var o = new Legacy();
        o.Value = 5;
        Console.WriteLine(o.Value + " " + o.Raw());
    }
}
