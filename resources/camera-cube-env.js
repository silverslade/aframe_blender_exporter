/**
 * Specifies an envMap on an entity, without replacing any existing material
 * properties.
 */
AFRAME.registerComponent('camera-cube-env', {
  schema: {
	    resolution: { type:'number', default: 128},
	    distance: {type:'number', default: 100000},
	    interval: { type:'number', default: 1000},
	    repeat: { type:'boolean', default: false}
	  },

	  /**
	   * Set if component needs multiple instancing.
	   */
	  multiple: false,

	  /**
	   * Called once when component is attached. Generally for initial setup.
	   */
	  init: function(){
	    this.counter = this.data.interval;
	    this.cam = new THREE.CubeCamera( 1.0, this.data.distance, this.data.resolution);
		
		this.cam.renderTarget.texture.minFilter = THREE.LinearMipMapLinearFilter;
		this.cam.renderTarget.texture.generateMipmaps = true;
	    this.el.object3D.add( this.cam );

	    this.done = false;
		var myCam = this.cam;
		var myEl = this.el;
		var myMesh = this.el.getObject3D('mesh');

		document.querySelector('a-scene').addEventListener('loaded', function (myCam, myEl, myMesh) {
			if(myMesh){
				myMesh.traverse( function( child ) { 
					if ( child instanceof THREE.Mesh ) {
						child.material.envMap = myCam.renderTarget.texture;
						child.material.needsUpdate = true;
					}
				});
			}
		});      
			  
	  },
	  
	  tick: function(t,dt){
		var myCam = this.cam;
	    if(!this.done){
	      if( this.counter > 0){
	        this.counter-=dt;
	      }else{
	        this.mesh = this.el.getObject3D('mesh');
	        
	        if(this.mesh){
	            this.mesh.visible = false;
				AFRAME.scenes[0].renderer.autoClear = true;
				// getWorldPosition FIX
	            myCam.position.copy(this.el.object3D.worldToLocal(this.el.object3D.getWorldPosition(myCam.position)));
	            myCam.update( AFRAME.scenes[0].renderer, this.el.sceneEl.object3D );

	            this.mesh.traverse( function( child ) { 
	                if ( child instanceof THREE.Mesh ){
						child.material.envMap = myCam.renderTarget.texture;
						child.material.needsUpdate = true;
					}
	            });
	            this.mesh.visible = true;
	        
	            if(!this.data.repeat){
	              this.done = true;
	              this.counter = this.data.interval;
	            }
	        }
	      }
	    }
	  },

	  /**
	   * Called when component is attached and when component data changes.
	   * Generally modifies the entity based on the data.
	   */
	  update: function (oldData) {
			this.counter = this.data.interval;
				this.cam = new THREE.CubeCamera( 1.0, this.data.distance, this.data.resolution);
			  this.cam.renderTarget.texture.minFilter = THREE.LinearMipMapLinearFilter;
	          this.el.object3D.add( this.cam );
	          this.done = false;
			  var myCam = this.cam;
			  
	          this.mesh = this.el.getObject3D('mesh');
	          if(this.mesh){
	            this.mesh.traverse( function( child ) { 
	                if ( child instanceof THREE.Mesh ) {
						child.material.envMap = myCam.renderTarget.texture;
						myCam.renderTarget.texture.generateMipmaps = true;
						child.material.needsUpdate = true;
					}
	            });
	          }
	  },

	  /**
	   * Called when a component is removed (e.g., via removeAttribute).
	   * Generally undoes all modifications to the entity.
	   */
	  remove: function () {},

	  /**
	   * Called on each scene tick.
	   */
	  // tick: function (t) { },

	  /**
	   * Called when entity pauses.
	   * Use to stop or remove any dynamic or background behavior such as events.
	   */
	  pause: function () { },

	  /**
	   * Called when entity resumes.
	   * Use to continue or add any dynamic or background behavior such as events.
	   */
	  play: function () { }
	});