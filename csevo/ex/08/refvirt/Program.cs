// 슬라이드 p8-v7-ref-virt — ref 반환은 시그니처의 일부다, C# 7.0
interface IS
{
    ref int Value();
}

class Base
{
    protected int v;
    public virtual ref int Get() { return ref v; }
}

class ByVal : Base, IS
{
    public override int Get() { return v; }       // drops the ref
    public int Value() { return v; }              // drops the ref
}

class App
{
    static void Main()
    {
    }
}
