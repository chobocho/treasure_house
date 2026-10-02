// 슬라이드 p10-v9-init-virtual — init 의 재정의와 구현, C# 9.0
using System;

class Base
{
    public virtual int Property { get; init; }
}

class C1 : Base
{
    public override int Property { get; init; }
}

#if BAD
class C2 : Base
{
    public override int Property { get; set; }   // set for init
}

interface IName { string Name { get; set; } }

class N : IName
{
    public string Name { get; init; }            // init for set
}
#endif

class App
{
    static void Main()
    {
        Base b = new C1 { Property = 1 };
        Console.WriteLine(b.Property);
    }
}
