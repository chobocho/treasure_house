// 슬라이드 p10-v9-cov-rules — 공변 반환이 안 되는 곳, C# 9.0
abstract class Base
{
    public abstract object Get();
    public abstract object Prop { get; set; }
}

class D : Base
{
    public override int Get() => 1;             // value type
    public override string Prop { get; set; }   // get and set
}

interface IShape { object Copy(); }

class Sq : IShape
{
    public string Copy() => "sq";               // interface
}

class App
{
    static void Main() { }
}
