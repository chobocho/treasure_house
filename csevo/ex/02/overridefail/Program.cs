// 슬라이드 p2-v1-overridefail — 고칠 수 없는 override, C# 1.0
class Base
{
    public void Plain() { }
    protected virtual void Hook() { }
    public virtual int Size() { return 0; }
}

class Derived : Base
{
    public override void Plain() { }        // not virtual
    public override void Hook() { }         // access changed
    public override long Size() { return 0; }   // return type changed
    public override void Missing() { }      // nothing to override
}

class App
{
    static void Main() { }
}
